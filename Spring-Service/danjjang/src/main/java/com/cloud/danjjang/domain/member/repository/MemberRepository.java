package com.cloud.danjjang.domain.member.repository;

import com.cloud.danjjang.domain.member.entity.Member;
import org.springframework.data.repository.CrudRepository;

import java.util.Optional;

public interface MemberRepository extends CrudRepository<Member, Long> {

    Optional<Member> findByEmail(String email);
    boolean existsByEmail(String email);
    Optional<Member> findById(Long memberId);
}
