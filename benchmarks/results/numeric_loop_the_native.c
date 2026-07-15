#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

static int64_t _the_main(void) {
    int64_t total = 0;
    int64_t _start_4 = 1, _end_4 = 5000000;
    int64_t _step_4 = _end_4 >= _start_4 ? 1 : -1;
    for (int64_t number = _start_4; _step_4 > 0 ? number <= _end_4 : number >= _end_4; number += _step_4) {
        total = total + number;
    }
    return total;
}

int main(void) {
    int64_t result = _the_main();
    printf("%" PRId64 "\n", (int64_t)(result));
    return 0;
}
