/*****************************************************************************
 * LEGALESE:   "Copyright (c) 2016, Dell Inc. All rights reserved."
 *
 * This source code is confidential, proprietary, and contains trade
 * secrets that are the sole property of Dell Inc.
 * Copy and/or distribution of this source code or disassembly or reverse
 * engineering of the resultant object code are strictly forbidden without
 * the written consent of Dell Inc.
 *
 *****************************************************************************/

/**
 * @file sys_utils_file_transfer.c
 * @brief  System utilities provide support for file transfers
 *****************************************************************************/
#define _SYS_UTILS_FILE_TRANSFER_C

#include "sys_utils_file_transfer.h"
#include "std_error_codes.h"
#include <curl/curl.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

typedef enum _sys_utils_error_type {
    sys_utils_std_error,
    sys_utils_curl_error
} _sys_utils_error_type;

/* CURL: data structure for file transfer statistics */
typedef struct _sys_utils_curl_progress {
    CURL *curl;         /* CURL file handle             */
} sys_utils_curl_progress_t;


/***************************************************************************
 * Function:    sys_utils_file_transfer_error()
 * 
 * Description: If the client requests, creates a descriptive string
 *              describing the state.  The return string is optional,
 *              and the client may not be interested in the return string.
 *
 * Parameters:  isStd  - TRUE if error is a standard error
 *                       FALSE if CURL error
 *              buffer - buffer (provided by caller) or NULL (uninterested)
 *              size   - size of buffer (ignored if buffer is NULL)
 **************************************************************************/
static void sys_utils_file_transfer_error( int isStd, int error, char *buffer, const int size )
{
    /* determine if calling client is interested in string description */
    if ( (buffer == NULL) || (size <= 0) ) {
        return;
    } else if ( isStd == sys_utils_std_error) {
        memset( buffer, 0, size );
        strerror_r( error, buffer, size );
    } else if ( isStd == sys_utils_curl_error ) {
        memset( buffer, 0, size );
        snprintf( buffer, size, "%s", curl_easy_strerror(error) );
    }
    return;
}

/***************************************************************************
 * @brief      Retrieves (download) a file from a remote source.
 * @param[in]  src_uri          - Source (remote) URI path of file
 * @param[in]  dst_uri          - Destination (local) path of file
 * @param[in]  password         - Password (if applicable) or NULL
 * @param[in]  progress_handler - Handler function for periodic updates
 * @param[in]  return_string    - (optional) buffer for return string (or NULL)
 * @param[in]  return_len       - (optional) size of return string buffer
 * @param[out] return_string    - (optional) string description of error
 * @returns     0 on success or error code on failure
 **************************************************************************/
static t_std_error sys_utils_file_retrieve_private(
        const char *src_uri, const char *dst_uri,
        char *password,
        int (*progress_handler)(void *, curl_off_t, curl_off_t, curl_off_t, curl_off_t),
        const char *post_buffer, int post_size,
        char *return_string, int return_len )
{
    CURL        *curl = NULL;
    t_std_error res = STD_ERR_OK;

    /* Initialize descriptor for transfer */
    curl = curl_easy_init();

    if (curl) {
        sys_utils_curl_progress_t prog;
        CURLcode                  csts = CURLE_OK;
        FILE                     *local_file = NULL;

        prog.curl = curl;

        /* Register the file to be transferred (RFC-3986 format) */
        curl_easy_setopt(curl, CURLOPT_URL, src_uri);

        /* Prepare the destination file */
        local_file = fopen(dst_uri, "wb");
        if (local_file == NULL) {
            /* FIXME: it may be easier to return the CURL corresponding error: CURLE_WRITE_ERROR */
            sys_utils_file_transfer_error( sys_utils_std_error, errno, return_string, return_len );
            curl_easy_cleanup( curl );
            return errno;
        }

        /* Install callback function for transfers (provides updates) */ 
        if (progress_handler) {

            /* Register the status API to receive transfer updates */
            curl_easy_setopt(curl, CURLOPT_XFERINFOFUNCTION, progress_handler);

            /* Pass the struct pointer to the callback */
            curl_easy_setopt(curl, CURLOPT_XFERINFODATA, &prog);
        }

        /* Send HTTP POST buffer to server */
        if ( (post_buffer != NULL) && (post_size > 0) ){

            /* post data to the server */
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_buffer);

            /* indicate size of buffer to be posted (for binary buffers) */
            curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, post_size);
        }

        /* configure the write callback for the local file */
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, local_file);

        /* Disable file transfer status from the curl library */
        curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 0L);

        /* request failure on HTTP failures */
        curl_easy_setopt(curl, CURLOPT_FAILONERROR, 1L);

        /* This blocks until complete */
        csts = curl_easy_perform(curl);

        /* Cleanup handles after completion */
        fclose(local_file);
        curl_easy_cleanup(curl);

        if (csts != CURLE_OK) {
            /* cleanup and remove the trashed file */
            unlink( dst_uri );
        }

        /* if wanted, convert the description string for the client */
        sys_utils_file_transfer_error( sys_utils_curl_error, csts, return_string, return_len );

        res = csts;
    }

    return res;
}


/***************************************************************************
 * @brief      Retrieves (download) a file from a remote source.
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
        const char *src_uri,
        const char *dst_uri,
        char *password,
        int (*progress_handler)(void *, curl_off_t, curl_off_t, curl_off_t, curl_off_t),
        char *return_string, int return_len )
{
    return( sys_utils_file_retrieve_private(src_uri, dst_uri, 
                                            password, 
                                            NULL, 
                                            NULL, 0,
                                            return_string, return_len) );
}


/***************************************************************************
 * @brief      Retrieves (download) a file from a remote source.
 * @param[in]  src_uri          - Source (remote) URI path of file
 * @param[in]  dst_uri          - Destination (local) path of file
 * @returns    0 on success or error code on failure
 **************************************************************************/
t_std_error sys_utils_file_retrieve_basic( const char *src_uri, const char *dst_uri )
{
    return( sys_utils_file_retrieve_private(src_uri, 
                                            dst_uri, 
                                            NULL, 
                                            NULL, 
                                            NULL, 0,
                                            NULL, 0) );
}


/***************************************************************************
 * @brief      Retrieves (download) a file from a remote source.
 * @param[in]  src_uri          - Source (remote) URI path of file
 * @param[in]  dst_uri          - Destination (local) path of file
 * @param[in]  post_buffer      - Buffer transmitted to POST server
 * @param[in]  post_buffer_len  - Size of buffer transmitted to POST server
 * @returns    0 on success or error code on failure
 **************************************************************************/
t_std_error sys_utils_file_retrieve_post( const char *src_uri, const char *dst_uri,
                                          const char *post_buffer, int post_size )
{
    return( sys_utils_file_retrieve_private(src_uri, dst_uri, 
                                            NULL, 
                                            NULL, 
                                            post_buffer, post_size,
                                            NULL, 0) );
}


/*************************************************************************/
/**                               EOF                                   **/
/*************************************************************************/

