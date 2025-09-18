package com.cloud.danjjang.domain.member.dto;

import com.cloud.danjjang.domain.enums.DiabetesType;
import com.cloud.danjjang.domain.enums.Gender;
import com.cloud.danjjang.domain.enums.Sensor;
import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

public class MemberSignDTO {

    @Getter
    public static class SignUpDTO {

        @NotBlank
        @Email(message = "유효한 이메일 주소를 입력해주세요.")
        String email;

        @NotBlank
        @Size(min = 8, max = 16, message = "비밀번호는 8자 이상 16자 이내여야 합니다.")
        @Pattern(regexp = "^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?]).*$",
                message = "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다.")
        String password;

        @NotBlank
        @Size(max = 10, message = "이름은 10자 이내여야 합니다.")
        String username;

        @NotNull
        LocalDate birth;

        @NotNull
        Float weight;

        @NotNull
        Float height;

        @NotNull
        Gender gender;

        @NotNull
        DiabetesType diabetesType;

        @NotNull
        Sensor sensor;
    }

    @Getter
    @AllArgsConstructor
    @NoArgsConstructor
    public static class LoginDTO {
        @NotBlank
        @Email(message = "유효한 이메일 주소를 입력해주세요.")
        String email;

        @NotBlank
        @Size(min = 8, max = 16, message = "비밀번호는 8자 이상 16자 이내여야 합니다.")
        @Pattern(regexp = "^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+\\-=\\[\\]{};':\"\\\\|,.<>\\/?]).*$",
                message = "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다.")
        String password;
    }

    @Getter
    @AllArgsConstructor
    @NoArgsConstructor
    public static class ParentLoginDTO {
        @NotBlank
        String code;

        @NotBlank
        @Size(max = 10, message = "이름은 10자 이내여야 합니다.")
        String name;
    }
}

