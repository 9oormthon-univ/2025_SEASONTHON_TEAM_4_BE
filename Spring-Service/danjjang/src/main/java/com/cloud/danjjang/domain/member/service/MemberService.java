package com.cloud.danjjang.domain.member.service;

import com.cloud.danjjang.common.apiPayload.code.status.ErrorCode;
import com.cloud.danjjang.common.exception.handler.GeneralHandler;
import com.cloud.danjjang.common.jwt.LoginService;
import com.cloud.danjjang.common.jwt.TokenDTO;
import com.cloud.danjjang.common.jwt.TokenProvider;
import com.cloud.danjjang.common.jwt.filter.JwtAuthenticationFilter;
import com.cloud.danjjang.domain.member.dto.MemberRequestDTO;
import com.cloud.danjjang.domain.member.dto.MemberResponseDTO;
import com.cloud.danjjang.domain.member.dto.MemberSignDTO;
import com.cloud.danjjang.domain.member.dto.RefreshTokenDTO;
import com.cloud.danjjang.domain.member.entity.Member;
import com.cloud.danjjang.domain.member.repository.MemberRepository;
import com.cloud.danjjang.domain.member.repository.RefreshRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Locale;

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
        final String code = CodeGenerator.next(10);

        Member newMember = MemberMapper.toLoginEmailMember(requestDto.getEmail(), passwordEncoder.encode(requestDto.getPassword()), requestDto.getUsername(), requestDto.getBirth(), requestDto.getWeight(), requestDto.getHeight(),
                requestDto.getGender(), requestDto.getDiabetesType(), requestDto.getSensor(), code);
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

    @Transactional(readOnly = true)
    public TokenDTO parentLoginByCode(String code, HttpServletResponse response) {
        Member member = memberRepository.findByCode(code)
                .orElseThrow(() -> new GeneralHandler(ErrorCode.MEMBER_NOT_FOUND));

        TokenDTO tokenDTO = tokenProvider.generateParentViewToken(member.getEmail(), member.getId());
        response.addHeader("Authorization", tokenDTO.getAccessToken());
        response.addHeader("X-Member-Id", String.valueOf(member.getId()));
        return tokenDTO;
    }

    public MemberResponseDTO.MyPageResponseDTO getMemberprofile(Member member) {
        return MemberResponseDTO.MyPageResponseDTO.builder()
                .username(member.getUsername())
                .height(member.getHeight())
                .weight(member.getWeight())
                .sensor(member.getSensor())
                .build();
    }

    public MemberResponseDTO.MemberSettingDTO profileSetting(Member member, MemberRequestDTO.MemberProfileDTO memberProfileDTO) {
        member.updateMember(
                memberProfileDTO.getUsername(),
                memberProfileDTO.getBirth(),
                memberProfileDTO.getGender(),
                memberProfileDTO.getHeight(),
                memberProfileDTO.getWeight());
        memberRepository.save(member);

        return MemberResponseDTO.MemberSettingDTO.builder()
                .memberId(member.getId())
                .build();
    }

    public MemberResponseDTO.MemberSettingDTO sensorSetting(Member member, MemberRequestDTO.MemberSensorDTO memberSensorDTO) {
        member.setSensor(memberSensorDTO.getSensor());
        memberRepository.save(member);

        return MemberResponseDTO.MemberSettingDTO.builder()
                .memberId(member.getId())
                .build();
    }

    public MemberResponseDTO.MemberSettingDTO passwordSetting(Member member, MemberRequestDTO.MemberPasswordDTO memberPasswordDTO) {
        member.setPassword(passwordEncoder.encode(memberPasswordDTO.getPassword()));
        memberRepository.save(member);

        return MemberResponseDTO.MemberSettingDTO.builder()
                .memberId(member.getId())
                .build();
    }
}

