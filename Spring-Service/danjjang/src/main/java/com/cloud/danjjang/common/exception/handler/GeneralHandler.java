package com.cloud.danjjang.common.exception.handler;

import com.cloud.danjjang.common.apiPayload.code.BaseErrorCode;
import com.cloud.danjjang.common.exception.GeneralException;

public class GeneralHandler extends GeneralException {

    public GeneralHandler(BaseErrorCode errorCode) {
        super(errorCode);
    }
}