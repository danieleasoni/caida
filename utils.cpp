#include "utils.h"

#include <string>
#include <unistd.h>
#include <ctime>

void timeval_sub(struct timeval* beginning, struct timeval *end,
                 struct timeval* res) {
    res->tv_sec = end->tv_sec - beginning->tv_sec;
    res->tv_usec = end->tv_usec - beginning->tv_usec;
    if (res->tv_usec < 0) {
        res->tv_usec += 1000000;
        res->tv_sec -= 1;
    }
}

std::string get_new_filename(std::string base_name, std::string ext) {
    std::string file_name = base_name + ext;
    unsigned int counter = 1;
    while (file_exists(file_name) && counter < 1000) {
        file_name = base_name + std::to_string(counter) + ext;
        counter++;
    }
    return file_name;
}

