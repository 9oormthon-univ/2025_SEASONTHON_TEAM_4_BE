package com.cloud.danjjang.domain.exercise.controller;

import com.cloud.danjjang.common.apiPayload.ApiResponse;
import com.cloud.danjjang.domain.exercise.dto.ExerciseRequestDTO;
import com.cloud.danjjang.domain.exercise.dto.ExerciseResponseDTO;
import com.cloud.danjjang.domain.exercise.service.ExerciseService;
import com.cloud.danjjang.domain.member.annotation.AuthUser;
import com.cloud.danjjang.domain.member.entity.Member;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.parameters.P;
import org.springframework.web.bind.annotation.*;

@Tag(name = "운동기록 API", description = "운동기록 관련 API입니다")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/exercise")
public class ExerciseController {
    private final ExerciseService exerciseService;

    @PostMapping("/save")
    @Operation(summary = "운동기록을 저장하는 API")
    public ApiResponse<ExerciseResponseDTO.ExerciseSaveDTO> saveExercise(@AuthUser Member member, @Valid @RequestBody ExerciseRequestDTO.ExerciseSaveDTO exerciseSaveDTO) {
        return ApiResponse.onSuccess(exerciseService.saveExercise(member, exerciseSaveDTO));
    }
}
