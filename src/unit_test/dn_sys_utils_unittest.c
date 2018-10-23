/************************************************************************
 * Copyright (c) 2016, Dell Inc.
 *
 * This source code is confidential, proprietary, and contains trade
 * secrets that are the sole property of Dell Inc.
 * Copy and/or distribution of this source code or disassembly or reverse
 * engineering of the resultant object code are strictly forbidden without
 * the written consent of Dell Inc.
 *
 * @file    dn_sys_utils_unittest.c
 * @date    July 2016
 * @brief   Unit test harness for system utilities
 */
#include <stdio.h>
#include <sys_utils_file_transfer.h>
#include "std_error_codes.h"

#define ERROR_STR_LEN   50

int main( int argc, char *argv[] )
{
    char        return_buffer[ERROR_STR_LEN];
    t_std_error return_code;

    if ( argc < 3 ) {
        printf("requires minimum of two arguments (source URI, local destination file)\n");
        return 0;
    } else {
        printf("source URI  : %s\n", argv[1]);
        printf("destination : %s\n", argv[2]);
    }

    return_code = sys_utils_file_retrieve_basic(argv[1], argv[2]);
    printf("\n\ntransfer %s (code %d)\n", 
            return_code == STD_ERR_OK ? "succeeded" : "failed", return_code);

    return_code = sys_utils_file_retrieve( argv[1], argv[2], 
            NULL, /* no password */
            NULL, /* no progress API */
            return_buffer, ERROR_STR_LEN);
            
    printf("\n\ntransfer %s\n", 
            return_code == STD_ERR_OK ? "succeeded" : "failed" );
    printf("return string: %s (code %d)\n", return_buffer, return_code);

    return 1;
}
