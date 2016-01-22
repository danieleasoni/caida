#ifndef NETSEC_CONSTANTS_H
#define NETSEC_CONSTANTS_H

/* TODO: Some of these should actually be configuration parameters, they should
 * be moved to some configuration file, and read at program start. For example,
 * boost.PropertyTree might be used to this end.
 */
namespace NSConstants {
    const int MaxFlowLifetime = 3600; // Max flow lifetime, in seconds
    // Max time of inactivity, in seconds, before a flow is expired
    const int MaxFlowInactiveTime = 60;
    const char * const FIELD_SEPARATOR = "\t";
}

#endif
