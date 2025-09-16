package com.cloud.danjjang.domain.member.dto;

import com.cloud.danjjang.domain.enums.Gender;
import com.cloud.danjjang.domain.enums.Sensor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

public class MemberResponseDTO {
    @Builder
    @Getter
    @AllArgsConstructor
    @NoArgsConstructor
    public static class MyPageResponseDTO {
        private String username;

        private Float height;

        private Float weight;

        private Sensor sensor;
    }

    @Getter
    @Builder
    public static class MemberSettingDTO {
        Long memberId;
    }
}
