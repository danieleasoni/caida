
#include <string>
#include <unistd.h>
#include <time.h>
#include "daniele_utils.h"

std::string get_new_filename(std::string base_name, std::string ext) {
    std::string file_name = base_name + ext;
    unsigned int counter = 1;
    while (file_exists(file_name) && counter < 1000) {
        file_name = base_name + std::to_string(counter) + ext;
        counter++;
    }
    return file_name;
}

