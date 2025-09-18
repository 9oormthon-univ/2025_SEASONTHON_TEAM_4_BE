package com.cloud.danjjang.domain.exercise.service;

import com.cloud.danjjang.common.apiPayload.code.status.ErrorCode;
import com.cloud.danjjang.common.exception.handler.GeneralHandler;
import com.cloud.danjjang.domain.exercise.dto.ExerciseRequestDTO;
import com.cloud.danjjang.domain.exercise.dto.ExerciseResponseDTO;
import com.cloud.danjjang.domain.exercise.entity.Exercise;
import com.cloud.danjjang.domain.exercise.repository.ExerciseRepository;
import com.cloud.danjjang.domain.member.entity.Member;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class ExerciseService {

    private final ExerciseRepository exerciseRepository;

    @Transactional
    public ExerciseResponseDTO.ExerciseSaveDTO saveExercise(Member member, ExerciseRequestDTO.ExerciseSaveDTO exerciseSaveDTO) {

        log.info("[exercise] save attempt memberId={} date={} startTime={} exerciseTime={} type={}",
                member.getId(), exerciseSaveDTO.getDate(), exerciseSaveDTO.getStartTime(), exerciseSaveDTO.getExerciseTime(), exerciseSaveDTO.getExerciseType());

        if (exerciseSaveDTO.getExerciseTime() != null && LocalTime.MIDNIGHT.equals(exerciseSaveDTO.getExerciseTime())) {
            log.warn("[exercise] invalid duration 00:00 memberId={} date={} startTime={}",
                    member.getId(), exerciseSaveDTO.getDate(), exerciseSaveDTO.getStartTime());
            throw new GeneralHandler(ErrorCode.INVALID_EXERCISE_TIME);
        }

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
        log.info("[exercise] saved exerciseId={} memberId={}", saved.getId(), member.getId());

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
        log.info("[exercise] get attempt memberId={} exerciseId={}", member.getId(), exerciseId);
        Exercise exercise = exerciseRepository
                .findByIdAndMember_Id(exerciseId, member.getId())
                .orElseThrow(() -> {
                    log.warn("[exercise] not found memberId={} exerciseId={}", member.getId(), exerciseId);
                    return new GeneralHandler(ErrorCode.EXERCISE_NOT_FOUND);
                });

        log.info("[exercise] get success memberId={} exerciseId={}", member.getId(), exercise.getId());

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
