package com.cloud.danjjang.domain.member.dto;

import com.cloud.danjjang.domain.enums.DiabetesType;
import com.cloud.danjjang.domain.enums.Gender;
import com.cloud.danjjang.domain.enums.Sensor;
import jakarta.validation.constraints.*;
import lombok.*;

import java.time.LocalDate;

public class MemberRequestDTO {

    @Getter
    @Builder
    @Setter
    @AllArgsConstructor
    @NoArgsConstructor
    public static class MemberProfileDTO {

        @NotBlank
        @Size(max = 10, message = "이름은 10자 이내여야 합니다.")
        String username;

        @NotNull
        LocalDate birth;

        @NotNull
        Gender gender;

        @NotNull
        Float weight;

        @NotNull
        Float height;
    }

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MemberSensorDTO {
        @NotNull
        Sensor sensor;
    }

    @Getter
    @Setter
    @Builder
    @AllArgsConstructor
    @NoArgsConstructor
    public static class MemberPasswordDTO {
        @NotBlank
        @Size(min = 8, max = 16, message = "비밀번호는 8자 이상 16자 이내여야 합니다.")
        @Pattern(regexp = "^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?]).*$",
                message = "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다.")
        String password;
    }
}
