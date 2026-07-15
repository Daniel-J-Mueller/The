#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    const int64_t limit = argc > 1 ? _strtoi64(argv[1], NULL, 10) : 5000000;
    int64_t total = 0;
    for (int64_t number = 1; number <= limit; ++number) {
        total = total + number;
    }
    printf("%" PRId64 "\n", total);
    return 0;
}
