package com.cloud.danjjang.domain.exercise.service;

import com.cloud.danjjang.domain.exercise.dto.ExerciseRequestDTO;
import com.cloud.danjjang.domain.exercise.dto.ExerciseResponseDTO;
import com.cloud.danjjang.domain.exercise.entity.Exercise;
import com.cloud.danjjang.domain.exercise.repository.ExerciseRepository;
import com.cloud.danjjang.domain.member.entity.Member;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ExerciseService {

    private final ExerciseRepository exerciseRepository;

    @Transactional
    public ExerciseResponseDTO.ExerciseSaveDTO saveExercise(Member member, ExerciseRequestDTO.ExerciseSaveDTO exerciseSaveDTO) {
        Exercise exercise = Exercise.builder()
                .title(exerciseSaveDTO.getTitle())
                .date(exerciseSaveDTO.getDate())
                .startTime(exerciseSaveDTO.getStartTime())
                .exerciseTime(exerciseSaveDTO.getExerciseTime())
                .exerciseType(exerciseSaveDTO.getExerciseType())
                .imagePath(null)
                .member(member)
                .build();

        Exercise saved = exerciseRepository.save(exercise);

        return ExerciseResponseDTO.ExerciseSaveDTO.builder()
                .exerciseId(saved.getId())
                .title(saved.getTitle())
                .date(saved.getDate())
                .startTime(saved.getStartTime())
                .exerciseTime(saved.getExerciseTime())
                .exerciseType(saved.getExerciseType())
                .build();
    }

    public ExerciseResponseDTO.ExerciseSaveDTO getExercise(Member member, Long exerciseId) {
        Exercise exercise = exerciseRepository
                .findByIdAndMember_Id(exerciseId, member.getId())
                .orElseThrow(() -> new IllegalArgumentException("운동 기록을 찾을 수 없습니다."));

        return ExerciseResponseDTO.ExerciseSaveDTO.builder()
                .exerciseId(exercise.getId())
                .title(exercise.getTitle())
                .date(exercise.getDate())
                .startTime(exercise.getStartTime())
                .exerciseTime(exercise.getExerciseTime())
                .exerciseType(exercise.getExerciseType())
                .build();
    }
}
