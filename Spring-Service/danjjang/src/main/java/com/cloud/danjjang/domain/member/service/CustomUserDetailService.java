package com.cloud.danjjang.domain.member.service;

import com.cloud.danjjang.domain.member.dto.CustomUserDetails;
import com.cloud.danjjang.domain.member.entity.Member;
import com.cloud.danjjang.domain.member.repository.MemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CustomUserDetailService implements UserDetailsService {

    private final MemberRepository memberRepository;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {

        Member member = memberRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("해당 아이디를 가진 사용자를 찾을 수 없습니다."));

        return new CustomUserDetails(member);
    }
}
