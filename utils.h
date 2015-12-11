#ifndef NETSEC_UTILS_H_
#define NETSEC_UTILS_H_

#include <string>
#include <unistd.h>
#include <time.h>

inline double timeval_to_seconds(struct timeval *tv) {
  return tv->tv_sec + double(tv->tv_usec)/1000000;
}

inline bool file_exists(const std::string& name) {
    return ( access ( name.c_str(), F_OK ) != -1 );
}

std::string get_new_filename(std::string base_name, std::string ext = "");

#endif // NETSEC_UTILS_H_
