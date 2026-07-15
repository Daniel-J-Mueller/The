#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { NAME_CAP = 128, ROW_CAP = 8192 };

typedef struct Name {
    char text[NAME_CAP];
    size_t line;
    struct Name *next;
} Name;

typedef struct {
    const char *path;
    Name *pages;
    Name *labels;
    Name *references;
    char page[NAME_CAP];
    char page_row[ROW_CAP];
    char proc[NAME_CAP];
    size_t iter_depth;
    unsigned version;
    unsigned versions;
    bool comment_block;
    bool line_comment;
    char delimiters[ROW_CAP];
    size_t depth;
    size_t errors;
} Linter;

typedef struct {
    char name[NAME_CAP];
    unsigned version;
    unsigned versions;
} Boundary;

static void diagnostic(Linter *linter, size_t line, size_t column,
                       const char *code, const char *message, const char *name) {
    fprintf(stderr, "%s:%zu:%zu: %s: ", linter->path, line, column, code);
    fprintf(stderr, message, name);
    fputc('\n', stderr);
    linter->errors++;
}

static bool name_start(char c) {
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_';
}

static bool name_rest(char c) {
    return name_start(c) || (c >= '0' && c <= '9');
}

static const char *space(const char *cursor) {
    while (*cursor == ' ' || *cursor == '\t' || *cursor == '\r') cursor++;
    return cursor;
}

static bool take_name(const char **cursor, char out[NAME_CAP]) {
    const char *at = *cursor;
    size_t length = 0;
    if (!name_start(*at)) return false;
    while (name_rest(*at)) {
        if (length + 1 >= NAME_CAP) return false;
        out[length++] = *at++;
    }
    out[length] = '\0';
    *cursor = at;
    return true;
}

static bool row_end(const char *cursor) {
    cursor = space(cursor);
    return *cursor == '\0' || *cursor == '\n' || *cursor == '|';
}

static bool take_uint(const char **cursor, unsigned *value) {
    uint64_t number = 0;
    if (**cursor < '0' || **cursor > '9') return false;
    while (**cursor >= '0' && **cursor <= '9') {
        number = number * 10u + (unsigned)(**cursor - '0');
        if (number > UINT32_MAX) return false;
        (*cursor)++;
    }
    *value = (unsigned)number;
    return true;
}

static bool boundary(const char *row, Boundary *out) {
    const char *cursor = row;
    memset(out, 0, sizeof(*out));
    if (strncmp(cursor, "PAGE ", 5) != 0) return false;
    cursor += 5;
    if (!take_name(&cursor, out->name)) return false;
    cursor = space(cursor);
    if (*cursor >= '0' && *cursor <= '9') {
        if (!take_uint(&cursor, &out->version)) return false;
        cursor = space(cursor);
        if (strncmp(cursor, "OF ", 3) != 0) return false;
        cursor += 3;
        if (!take_uint(&cursor, &out->versions)) return false;
    }
    return row_end(cursor);
}

static void copy_row(char out[ROW_CAP], const char *row) {
    size_t length = strcspn(row, "\r\n");
    memcpy(out, row, length);
    out[length] = '\0';
}

static uint64_t page_id(const char *name) {
    uint64_t hash = UINT64_C(14695981039346656037);
    while (*name) {
        hash ^= (unsigned char)*name++;
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static Name *find_page_id(Name *pages, const char *name) {
    uint64_t id = page_id(name);
    while (pages) {
        if (page_id(pages->text) == id && strcmp(pages->text, name) != 0) return pages;
        pages = pages->next;
    }
    return NULL;
}

static Name *find(Name *names, const char *text) {
    while (names) {
        if (strcmp(names->text, text) == 0) return names;
        names = names->next;
    }
    return NULL;
}

static bool add(Name **names, const char *text, size_t line) {
    Name *name = malloc(sizeof(*name));
    if (!name) return false;
    memcpy(name->text, text, strlen(text) + 1);
    name->line = line;
    name->next = *names;
    *names = name;
    return true;
}

static void clear(Name **names) {
    while (*names) {
        Name *next = (*names)->next;
        free(*names);
        *names = next;
    }
}

static void resolve(Linter *linter) {
    Name *reference = linter->references;
    while (reference) {
        if (!find(linter->labels, reference->text))
            diagnostic(linter, reference->line, 1, "E004",
                       "unknown line @%s", reference->text);
        reference = reference->next;
    }
    clear(&linter->labels);
    clear(&linter->references);
}

static size_t block_marks(const char *row) {
    size_t count = 0;
    while ((row = strstr(row, "||")) != NULL) {
        count++;
        row += 2;
    }
    return count;
}

static bool truncated(const char *row) {
    size_t length = strcspn(row, "\r\n");
    while (length && (row[length - 1] == ' ' || row[length - 1] == '\t')) length--;
    return length >= 2 && row[length - 1] == '.' && row[length - 2] == '.';
}

static const char *line_comment(const char *row) {
    bool quoted = false;
    char quote = '\0';
    for (const char *cursor = row; *cursor && *cursor != '\n'; cursor++) {
        if (quoted) {
            if (*cursor == '\\' && cursor[1]) cursor++;
            else if (*cursor == quote) quoted = false;
            continue;
        }
        if (*cursor == '\'' || *cursor == '"') { quoted = true; quote = *cursor; continue; }
        if (cursor[0] == '|' && cursor[1] != '|') return cursor;
    }
    return NULL;
}

static void lint_delimiters(Linter *linter, const char *row, size_t line) {
    bool quoted = false;
    char quote = '\0';
    for (size_t column = 0; row[column] && row[column] != '\n'; column++) {
        char c = row[column];
        if (quoted) {
            if (c == '\\' && row[column + 1]) column++;
            else if (c == quote) quoted = false;
            continue;
        }
        if (c == '\'' || c == '"') { quoted = true; quote = c; continue; }
        if (c == '|') break;
        if (c == '(' || c == '[' || c == '{') {
            if (linter->depth < ROW_CAP) linter->delimiters[linter->depth++] = c;
            continue;
        }
        if (c == ')' || c == ']' || c == '}') {
            char expected = c == ')' ? '(' : c == ']' ? '[' : '{';
            if (!linter->depth || linter->delimiters[linter->depth - 1] != expected)
                diagnostic(linter, line, column + 1, "E010", "unmatched closing delimiter %s",
                           c == ')' ? ")" : c == ']' ? "]" : "}");
            else linter->depth--;
        }
    }
}

static bool operation(const char *cursor, const char *word) {
    size_t length = strlen(word);
    return strncmp(cursor, word, length) == 0 &&
           (cursor[length] == ' ' || cursor[length] == '\t');
}

static void lint_operation(Linter *linter, const char *cursor, size_t line) {
    char name[NAME_CAP];
    if (operation(cursor, "OBJ")) {
        cursor = space(cursor + 3);
        if (!take_name(&cursor, name) || *(cursor = space(cursor)) != '=' ||
            !*space(cursor + 1))
            diagnostic(linter, line, 1, "E012", "expected OBJ name = value%s", "");
    } else if (operation(cursor, "RUN")) {
        cursor = space(cursor + 3);
        if (!take_name(&cursor, name) ||
            strncmp((cursor = space(cursor)), "through ", 8) != 0 ||
            *space(cursor + 8) != '(')
            diagnostic(linter, line, 1, "E012", "expected RUN name through (first, last)%s", "");
    } else if (operation(cursor, "ITER")) {
        cursor = space(cursor + 4);
        if (!take_name(&cursor, name)) {
            diagnostic(linter, line, 1, "E012", "expected ITER name and iterator%s", "");
            return;
        }
        cursor = space(cursor);
        if (strncmp(cursor, "intthrough ", 11) == 0) cursor = space(cursor + 11);
        else if (strncmp(cursor, "stridethrough ", 14) == 0) cursor = space(cursor + 14);
        else if (strncmp(cursor, "in ", 3) == 0) cursor = space(cursor + 3);
        else {
            diagnostic(linter, line, 1, "E012", "unknown ITER form for %s", name);
            return;
        }
        if (!*cursor)
            diagnostic(linter, line, 1, "E012", "ITER has no input for %s", name);
    } else if (operation(cursor, "PUT")) {
        char target[NAME_CAP];
        cursor = space(cursor + 3);
        if (!take_name(&cursor, name) || strncmp((cursor = space(cursor)), "into ", 5) != 0) {
            diagnostic(linter, line, 1, "E012", "expected PUT value into target%s", "");
            return;
        }
        cursor = space(cursor + 5);
        if (!take_name(&cursor, target)) {
            diagnostic(linter, line, 1, "E012", "PUT has no target for %s", name);
            return;
        }
        cursor = space(cursor);
        if (strncmp(cursor, "at ", 3) == 0) {
            cursor = space(cursor + 3);
            if (strncmp(cursor, "end", 3) == 0 && !name_rest(cursor[3])) cursor += 3;
            else if (strncmp(cursor, "beginning", 9) == 0 && !name_rest(cursor[9])) cursor += 9;
            else if (strncmp(cursor, "value", 5) == 0 && !name_rest(cursor[5])) cursor += 5;
            else {
                diagnostic(linter, line, 1, "E012", "PUT position must be end, beginning, or value for %s", target);
                return;
            }
        }
        if (!row_end(cursor))
            diagnostic(linter, line, 1, "E012", "unexpected text after PUT target %s", target);
    }
}

static bool record_references(Linter *linter, const char *row, size_t line) {
    const char *cursor = row;
    while (*cursor && *cursor != '|') {
        if (cursor[0] == '-' && cursor[1] == '>') {
            char name[NAME_CAP];
            cursor = space(cursor + 2);
            const char *target = cursor + 1;
            if (*cursor == '@' && take_name(&target, name)) {
                if (!add(&linter->references, name, line)) return false;
            }
        }
        if (*cursor) cursor++;
    }
    return true;
}

static bool lint_row(Linter *linter, const char *row, size_t line) {
    const char *cursor = space(row);
    char name[NAME_CAP];
    Boundary mark;

    if (linter->line_comment) {
        linter->line_comment = truncated(row);
        return true;
    }

    if (linter->comment_block) {
        if (block_marks(row) % 2u) linter->comment_block = false;
        return true;
    }
    if (cursor[0] == '|' && cursor[1] == '|') {
        if (block_marks(row) % 2u) linter->comment_block = true;
        return true;
    }
    {
        const char *comment = line_comment(row);
        if (comment && truncated(comment)) linter->line_comment = true;
    }
    if (*cursor == '|') return true;

    if (operation(cursor, "PAGEEND")) {
        cursor = space(cursor + 7);
        if (!take_name(&cursor, name) || !row_end(cursor))
            diagnostic(linter, line, 1, "E005", "expected PAGEEND name%s", "");
        else if (!linter->page[0] || strcmp(name, linter->page) != 0)
            diagnostic(linter, line, 1, "E001", "PAGEEND does not match PAGE %s",
                       linter->page[0] ? linter->page : name);
        else if (linter->proc[0])
            diagnostic(linter, line, 1, "E013", "PAGE ended inside PROC %s", linter->proc);
        else {
            resolve(linter);
            linter->page[0] = linter->page_row[0] = '\0';
            linter->version = linter->versions = 0;
        }
        return true;
    }

    if (operation(cursor, "PROCEND") || strcmp(cursor, "PROCEND\n") == 0 || strcmp(cursor, "PROCEND") == 0) {
        if (!linter->proc[0]) diagnostic(linter, line, 1, "E013", "PROCEND without PROC%s", "");
        else if (linter->iter_depth) diagnostic(linter, line, 1, "E013", "PROC ended inside ITER %s", linter->proc);
        else linter->proc[0] = '\0';
        return true;
    }

    if (operation(cursor, "ITEREND") || strcmp(cursor, "ITEREND\n") == 0 || strcmp(cursor, "ITEREND") == 0) {
        if (!linter->iter_depth) diagnostic(linter, line, 1, "E013", "ITEREND without ITER%s", "");
        else linter->iter_depth--;
        return true;
    }

    if (operation(cursor, "PROC")) {
        const char *declaration = space(cursor + 4);
        if (!take_name(&declaration, name))
            diagnostic(linter, line, 1, "E012", "expected PROC name%s", "");
        else if (linter->proc[0])
            diagnostic(linter, line, 1, "E013", "nested PROC %s", name);
        else memcpy(linter->proc, name, strlen(name) + 1);
        return true;
    }

    if (strncmp(row, "PAGE", 4) == 0 || strncmp(cursor, "PAGE", 4) == 0) {
        if (!boundary(row, &mark)) {
            diagnostic(linter, line, 1, "E005", "PAGE row must begin exactly 'PAGE ' and contain a valid identifier%s", "");
            return true;
        }
        if (linter->page[0]) {
            diagnostic(linter, line, 1, "E002", "nested PAGE %s", mark.name);
        } else {
            Name *collision;
            resolve(linter);
            if ((mark.version == 0) != (mark.versions == 0) || mark.version > mark.versions)
                diagnostic(linter, line, 1, "E007", "invalid degradation schedule %s", mark.name);
            if (find(linter->pages, mark.name))
                diagnostic(linter, line, 1, "E003", "duplicate PAGE identifier %s", mark.name);
            collision = find_page_id(linter->pages, mark.name);
            if (collision)
                diagnostic(linter, line, 1, "E009", "PAGE identifier hash collision for %s", mark.name);
            if (!add(&linter->pages, mark.name, line)) return false;
            memcpy(linter->page, mark.name, strlen(mark.name) + 1);
            copy_row(linter->page_row, row);
            linter->version = mark.version;
            linter->versions = mark.versions;
            if (getenv("THE_LINT_IDS"))
                fprintf(stdout, "%s:%zu: PAGE %s = %016llx\n", linter->path, line,
                        mark.name, (unsigned long long)page_id(mark.name));
        }
        return true;
    }

    if (operation(cursor, "ITER")) linter->iter_depth++;

    if (*cursor == '@') {
        cursor++;
        if (!take_name(&cursor, name) || !row_end(cursor)) {
            diagnostic(linter, line, 1, "E005", "malformed line label%s", "");
            return true;
        }
        if (find(linter->labels, name))
            diagnostic(linter, line, 1, "E003", "duplicate line @%s", name);
        else if (!add(&linter->labels, name, line)) return false;
    }
    lint_operation(linter, cursor, line);
    lint_delimiters(linter, row, line);
    return record_references(linter, row, line);
}

static void highlight(const char *row, size_t line, bool comment_block, bool line_continuation) {
    const char *cursor = space(row);
    const char *color = NULL;
    char gradient[32];
    Boundary mark;
    if (comment_block || line_continuation || (cursor[0] == '|' && cursor[1] == '|') || *cursor == '|') {
        color = "\x1b[90m";
    } else if (boundary(row, &mark) && mark.version && mark.versions) {
        unsigned red = mark.versions == 1 ? 0 : 255u * (mark.version - 1u) / (mark.versions - 1u);
        unsigned green = 255u - red;
        snprintf(gradient, sizeof(gradient), "\x1b[38;2;%u;%u;0m", red, green);
        color = gradient;
    } else if (strncmp(row, "PAGE ", 5) == 0) color = "\x1b[35m";
    else if (*cursor == '@') color = "\x1b[36m";
    else if (strstr(cursor, "-> @")) color = "\x1b[33m";
    printf("%4zu | %s%s%s", line, color ? color : "", row, color ? "\x1b[0m" : "");
    if (!strchr(row, '\n')) putchar('\n');
}

static int lint_file(const char *path, bool color) {
    FILE *file;
    char row[ROW_CAP];
    size_t line = 0;
    Linter linter = {0};
    linter.path = path;

    file = fopen(path, "rb");
    if (!file) {
        fprintf(stderr, "%s: %s\n", path, strerror(errno));
        return 2;
    }
    while (fgets(row, sizeof(row), file)) {
        line++;
        if (!strchr(row, '\n') && !feof(file)) {
            diagnostic(&linter, line, 1, "E006", "physical line exceeds limit%s", "");
            while (fgets(row, sizeof(row), file) && !strchr(row, '\n')) {}
            continue;
        }
        if (color) highlight(row, line, linter.comment_block, linter.line_comment);
        if (!lint_row(&linter, row, line)) {
            fprintf(stderr, "%s: allocation failed\n", path);
            fclose(file);
            clear(&linter.pages); clear(&linter.labels); clear(&linter.references);
            return 2;
        }
    }
    if (ferror(file)) {
        fprintf(stderr, "%s: read failed\n", path);
        fclose(file);
        return 2;
    }
    fclose(file);
    if (linter.page[0])
        diagnostic(&linter, line ? line : 1, 1, "E001", "unclosed PAGE %s", linter.page);
    if (linter.proc[0])
        diagnostic(&linter, line ? line : 1, 1, "E013", "unclosed PROC %s", linter.proc);
    if (linter.iter_depth)
        diagnostic(&linter, line ? line : 1, 1, "E013", "unclosed ITER blocks%s", "");
    if (linter.comment_block)
        diagnostic(&linter, line ? line : 1, 1, "E008", "unclosed comment block%s", "");
    if (linter.line_comment)
        diagnostic(&linter, line ? line : 1, 1, "E014", "line continuation reaches end of file%s", "");
    if (linter.depth)
        diagnostic(&linter, line ? line : 1, 1, "E011", "unclosed delimiter %s",
                   linter.delimiters[linter.depth - 1] == '(' ? "(" :
                   linter.delimiters[linter.depth - 1] == '[' ? "[" : "{");
    resolve(&linter);
    clear(&linter.pages);
    return linter.errors ? 1 : 0;
}

int main(int argc, char **argv) {
    bool color = false;
    int first = 1;
    int result = 0;

    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        puts("the-lint 0.1.1");
        return 0;
    }
    if (argc == 2 && (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0)) {
        puts("usage: the-lint [--color] FILE.the [FILE.the ...]");
        puts("exit 0: clean, 1: diagnostics, 2: invocation or input failure");
        return 0;
    }
    if (first < argc && strcmp(argv[first], "--color") == 0) {
        color = true;
        first++;
    }
    if (first == argc) {
        fprintf(stderr, "usage: the-lint [--color] FILE.the [FILE.the ...]\n");
        return 2;
    }

    for (int index = first; index < argc; index++) {
        const char *path = argv[index];
        size_t length = strlen(path);
        int status;
        if (length < 4 || strcmp(path + length - 4, ".the") != 0) {
            fprintf(stderr, "%s:1:1: E000: expected .the source\n", path);
            result = 2;
            continue;
        }
        status = lint_file(path, color);
        if (status > result) result = status;
    }
    return result;
}
