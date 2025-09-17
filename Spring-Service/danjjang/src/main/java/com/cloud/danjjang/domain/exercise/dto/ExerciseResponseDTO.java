package com.cloud.danjjang.domain.exercise.dto;

import com.cloud.danjjang.domain.enums.ExerciseType;
import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.validation.constraints.NotNull;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDate;
import java.time.LocalTime;

public class ExerciseResponseDTO {

    @Getter
    @Builder
    public static class ExerciseSaveDTO {
        private Long exerciseId;

        private String title;

        private LocalDate date;

        private LocalTime startTime;

        private LocalTime exerciseTime;

        private ExerciseType exerciseType;
    }
}
