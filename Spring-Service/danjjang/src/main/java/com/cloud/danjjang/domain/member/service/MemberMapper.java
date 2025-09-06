package com.cloud.danjjang.domain.member.service;

import com.cloud.danjjang.domain.enums.DiabetesType;
import com.cloud.danjjang.domain.enums.Gender;
import com.cloud.danjjang.domain.enums.Sensor;
import com.cloud.danjjang.domain.member.dto.RefreshTokenDTO;
import com.cloud.danjjang.domain.member.entity.Member;

public class MemberMapper {

    public static Member toLoginEmailMember(String email, String encodedPassword, String username, Long birth,
                                            Float weight, Float height, Gender gender, DiabetesType diabetesType,
                                            Sensor sensor, String code) {
        return Member.builder()
                .email(email)
                .password(encodedPassword)
                .username(username)
                .birth(birth)
                .weight(weight)
                .height(height)
                .gender(gender)
                .diabetesType(diabetesType)
                .sensor(sensor)
                .code(code)
                .build();
    }

    public static RefreshTokenDTO toRefreshToken(String refreshToken) {
        return RefreshTokenDTO.builder()
                .refreshToken(refreshToken)
                .build();
    }
}
