package com.cloud.danjjang.domain.member.service;

import com.cloud.danjjang.common.apiPayload.code.status.ErrorCode;
import com.cloud.danjjang.common.exception.handler.GeneralHandler;
import com.cloud.danjjang.common.jwt.LoginService;
import com.cloud.danjjang.common.jwt.TokenProvider;
import com.cloud.danjjang.common.jwt.filter.JwtAuthenticationFilter;
import com.cloud.danjjang.domain.member.dto.MemberSignDTO;
import com.cloud.danjjang.domain.member.dto.RefreshTokenDTO;
import com.cloud.danjjang.domain.member.entity.Member;
import com.cloud.danjjang.domain.member.repository.MemberRepository;
import com.cloud.danjjang.domain.member.repository.RefreshRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
@Service
@RequiredArgsConstructor

public class MemberService {

    private final MemberRepository memberRepository;
    private final TokenProvider tokenProvider;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final PasswordEncoder passwordEncoder;
    private final RefreshRepository refreshRepository;
    private final LoginService loginService;

    @Transactional
    public RefreshTokenDTO insertMember(HttpServletResponse response, MemberSignDTO.SignUpDTO requestDto) {

        if (memberRepository.existsByEmail(requestDto.getEmail())) {
            throw new GeneralHandler(ErrorCode.ID_ALREADY_EXIST);
        }

        Member newMember = MemberMapper.toLoginEmailMember(requestDto.getEmail(), passwordEncoder.encode(requestDto.getPassword()), requestDto.getUsername(), requestDto.getBirth(), requestDto.getWeight(), requestDto.getHeight(), requestDto.getGender(), requestDto.getDiabetesType(), requestDto.getSensor());
        Member savedMember = memberRepository.save(newMember);

        return RefreshTokenDTO.builder()
                .memberId(savedMember.getId())
                .refreshToken(issueToken(savedMember.getEmail(), response)).build();
    }

    private String issueToken(String email, HttpServletResponse response) {
        String newAccessToken = loginService.issueAccessToken(email);
        String newRefreshToken = loginService.issueRefreshToken(email);
        response.addHeader("Authorization", newAccessToken);
        return newRefreshToken;
    }

    @Transactional
    public String reissueToken(HttpServletRequest request, HttpServletResponse response) {
        String refreshToken = jwtAuthenticationFilter.resolveToken(request);

        String username  = tokenProvider.getAuthenticationFromAccessToken(refreshToken).getName();
        String newAccessToken = loginService.issueAccessToken(username);
        String newRefreshToken = loginService.reissueRefreshToken(username, refreshToken);

        response.addHeader("Authorization", newAccessToken);
        return newRefreshToken;
    }

}

