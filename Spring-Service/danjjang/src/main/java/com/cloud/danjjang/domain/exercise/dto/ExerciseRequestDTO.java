package com.cloud.danjjang.domain.exercise.dto;

import com.cloud.danjjang.domain.enums.ExerciseType;
import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalTime;

public class ExerciseRequestDTO {

    @Getter
    public static class ExerciseSaveDTO {
        @NotBlank
        @Size(max = 10, message = "제목은 10자 이내여야 합니다.")
        private String title;

        @NotNull
        @JsonFormat(pattern = "yyyy-MM-dd")
        private LocalDate date;

        @NotNull
        @JsonFormat(pattern = "HH:mm")
        private LocalTime startTime;

        @NotNull
        @JsonFormat(pattern = "HH:mm")
        private LocalTime exerciseTime;

        @NotNull
        private ExerciseType exerciseType;
    }

}
