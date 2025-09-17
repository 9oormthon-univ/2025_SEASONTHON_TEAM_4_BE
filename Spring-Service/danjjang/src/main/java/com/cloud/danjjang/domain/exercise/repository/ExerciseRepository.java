package com.cloud.danjjang.domain.exercise.repository;

import com.cloud.danjjang.domain.exercise.entity.Exercise;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ExerciseRepository extends JpaRepository<Exercise, Long> {
}
