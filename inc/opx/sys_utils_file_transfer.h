/*
 * Copyright (c) 2016 Dell Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 *
 * THIS CODE IS PROVIDED ON AN  *AS IS* BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
 *  LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
 * FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
 *
 * See the Apache Version 2.0 License for specific language governing
 * permissions and limitations under the License.
 */

/**
 *       @file  sys_utils_file_transfer.h
 *      @brief  Retrieves (download) a file from a remote source.
 *   @internal
 *
 *     Created  07/01/2016
 *     Company  DELL
 *   Copyright  Copyright (c) 2016
 *
 * =====================================================================================
 */
#ifndef _SYS_UTILS_FILE_TRANSFER_H
#define _SYS_UTILS_FILE_TRANSFER_H

#include "std_error_codes.h"
#include <curl/curl.h>

#ifdef __cplusplus
extern "C" {
#endif

/***************************************************************************
 * @brief      Retrieves (downloads) a file from a remote source.
 * @param[in]  src_uri          - Source (remote) URI path of file
 * @param[in]  dst_uri          - Destination (local) path of file
 * @param[in]  password         - Password (if applicable) or NULL
 * @param[in]  progress_handler - Handler function for periodic updates
 * @param[in]  return_string    - (optional) buffer for return string (or NULL)
 * @param[in]  return_len       - (optional) size of return string buffer
 * @param[out] return_string    - (optional) string description of error
 * @returns     0 on success or error code on failure
 **************************************************************************/
t_std_error sys_utils_file_retrieve( 
        const char *src_uri, const char *dst_uri,
        char *password,
        int (*progress_handler)(void *, curl_off_t, curl_off_t, curl_off_t, curl_off_t),
        char *return_string, int return_len );

/***************************************************************************
 * @brief      Retrieves (downloads) a file from a remote source.
 * @param[in]  src_uri - Source (remote) URI path of file
 * @param[in]  dst_uri - Destination (local) path of file
 * @returns    0 on success or error code on failure
 **************************************************************************/
t_std_error sys_utils_file_retrieve_basic( const char *src_uri, const char *dst_uri );


/***************************************************************************
 * @brief      Retrieves (download) a file from a remote source.
 * @param[in]  src_uri          - Source (remote) URI path of file
 * @param[in]  dst_uri          - Destination (local) path of file
 * @param[in]  post_buffer      - Buffer transmitted to POST server
 * @param[in]  post_buffer_len  - Size of buffer transmitted to POST server
 * @returns    0 on success or error code on failure
 **************************************************************************/
t_std_error sys_utils_file_retrieve_post( const char *src_uri, const char *dst_uri,
                                          const char *post_buffer, int post_size );
#ifdef __cplusplus
}
#endif

#endif  /* _SYS_UTILS_FILE_TRANSFER_H  */

