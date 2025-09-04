package com.cloud.danjjang.common.apiPayload.code.status;

import com.cloud.danjjang.common.apiPayload.code.BaseCode;
import com.cloud.danjjang.common.apiPayload.code.ReasonDTO;
import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
@AllArgsConstructor
public enum SuccessCode implements BaseCode {

    _OK(HttpStatus.OK,"COMMON200", "성공적으로 요청을 수행하였습니다."),

    // 회원가입 응답
    _SIGNUP_SUCCESS(HttpStatus.OK, "SIGNUP200", "회원가입 성공입니다."),
    _LOGIN_SUCCESS(HttpStatus.OK, "LOGIN200", "로그인 성공입니다."),

    CREATED(HttpStatus.CREATED,"COMMON201", "성공적으로 생성하였습니다."),
    NO_CONTENT(HttpStatus.NO_CONTENT,"COMMON204", "성공적으로 삭제하였습니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

    @Override
    public ReasonDTO getReason() {
        return ReasonDTO.builder()
                .message(message)
                .code(code)
                .isSuccess(true)
                .build();
    }

    @Override
    public ReasonDTO getReasonHttpStatus() {
        return ReasonDTO.builder()
                .message(message)
                .code(code)
                .isSuccess(true)
                .httpStatus(httpStatus)
                .build();
    }
}

