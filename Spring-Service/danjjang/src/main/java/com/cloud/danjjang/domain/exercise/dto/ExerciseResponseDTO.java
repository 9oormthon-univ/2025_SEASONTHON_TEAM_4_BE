package com.cloud.danjjang.domain.exercise.dto;

import lombok.Builder;
import lombok.Getter;

public class ExerciseResponseDTO {

    @Getter
    @Builder
    public static class ExerciseSaveDTO {
        Long exerciseId;
    }
}
