package com.cloud.danjjang.domain.exercise.repository;

import com.cloud.danjjang.domain.exercise.entity.Exercise;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ExerciseRepository extends JpaRepository<Exercise, Long> {
    Optional<Exercise> findByIdAndMember_Id(Long id, Long memberId);
}
