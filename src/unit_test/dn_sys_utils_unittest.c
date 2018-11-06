/*
 * Copyright (c) 2016 Dell Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 *
 * THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
 * LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
 * FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
 *
 * See the Apache Version 2.0 License for specific language governing
 * permissions and limitations under the License.
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
