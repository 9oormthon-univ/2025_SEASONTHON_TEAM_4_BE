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
        @Size(max = 10)
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
}
