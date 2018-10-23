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

#include "sys_utils_file_transfer.h"
#include "std_error_codes.h"

#include <gtest/gtest.h>
#include <stdio.h>

#define ERROR_STR_LEN   50

static bool test_file_retrieve_basic_T()
{ 
    t_std_error return_code;

    return_code = sys_utils_file_retrieve_basic(
                  "https://www.python.org/ftp/python/2.7.14/python-2.7.14.msi", 
                  "python-2.7.14.msi");
    return return_code == STD_ERR_OK;
}

static bool test_file_retrieve_T()
{ 
    char return_buffer[ERROR_STR_LEN];
    t_std_error return_code;
    return_code = sys_utils_file_retrieve(
            "https://www.python.org/ftp/python/2.7.14/python-2.7.14.msi", 
            "python-2.7.14.msi", 
            NULL, 
            NULL, 
            return_buffer, ERROR_STR_LEN);
 
    return return_code == STD_ERR_OK;
}

static bool test_file_retrieve_basic_F()
{ 
    t_std_error return_code;

    return_code = sys_utils_file_retrieve_basic(
                  "http://build-eqx-01.force10networks.com//tftpboot/NGOS/engineering-release/AmazonInstallers/banana", 
                  "gee.wally");
    return return_code == STD_ERR_OK;
}

static bool test_file_retrieve_F()
{ 
    char return_buffer[ERROR_STR_LEN];
    t_std_error return_code;
    return_code = sys_utils_file_retrieve(
            "http://build-eqx-01.force10networks.com//tftpboot/NGOS/engineering-release/AmazonInstallers/banana", 
            "gee.wally", 
            NULL, /* no password */
            NULL, /* no progress API */
            return_buffer, ERROR_STR_LEN);
 
    return return_code == STD_ERR_OK;
}


TEST(sys_utils_file_retrieve_test_true, operation)
{
    EXPECT_TRUE(test_file_retrieve_basic_T());
    EXPECT_TRUE(test_file_retrieve_T());
}

TEST(sys_utils_file_retrieve_test_false, operation)
{
    EXPECT_FALSE(test_file_retrieve_basic_F());
    EXPECT_FALSE(test_file_retrieve_F());
}



int main( int argc, char *argv[] )
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
