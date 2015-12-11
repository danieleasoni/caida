#ifndef NETSEC_UTILS_H_
#define NETSEC_UTILS_H_

#include <string>
#include <unistd.h>
#include <ctime>

// Convert a timeval structure to seconds (float)
inline double timeval_to_seconds(const struct timeval *tv) {
  return tv->tv_sec + double(tv->tv_usec)/1000000;
}

// Subtracts the time value in end from the time value in end from the time
// value in beginning, and places the difference in the timeval pointed to
// by res. The result is normalized such that res->tv_usec has a value in the
// range 0 to 999,999.
//
// This definition is taken from the timersub manpage (bsd).
void timeval_sub(const struct timeval* beginning, const struct timeval *end,
                 struct timeval* res);

inline bool file_exists(const std::string& name) {
    return ( access ( name.c_str(), F_OK ) != -1 );
}

// Returns a filename (with given extension, if any) that *probably* does not
// exist. Note that this function performs no locking and is therefore
// NOT THREAD SAFE!
std::string get_new_filename(std::string base_name, std::string ext = "");

#endif // NETSEC_UTILS_H_
