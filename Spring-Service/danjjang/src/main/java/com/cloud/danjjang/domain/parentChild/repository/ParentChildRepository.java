package com.cloud.danjjang.domain.parentChild.repository;

import com.cloud.danjjang.domain.parentChild.entity.ParentChild;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ParentChildRepository extends JpaRepository<ParentChild, Long> {
}
