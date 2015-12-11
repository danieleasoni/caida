#ifndef NETSEC_CONSTANTS_H
#define NETSEC_CONSTANTS_H

/* TODO: Some of these should actually be configuration parameters, they should
 * be moved to some configuration file, and read at program start. For example,
 * boost.PropertyTree might be used to this end.
 */
namespace NSConstants {
    const int MaxFlowLifetime = 60; // Max flow lifetime, in seconds
    const char * const FIELD_SEPARATOR = "\t";
}

#endif
