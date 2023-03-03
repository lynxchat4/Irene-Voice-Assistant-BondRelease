#pragma once

#include "config.h"

#ifdef LOGGING_PORT

#define log_print(str) LOGGING_PORT.print(str)
#define log_println(str) LOGGING_PORT.println(str)
#define log_format(format, args...) LOGGING_PORT.printf(format, args)

#else

#define log_print(str)
#define log_println(str)
#define log_format(format, args...)

#endif
