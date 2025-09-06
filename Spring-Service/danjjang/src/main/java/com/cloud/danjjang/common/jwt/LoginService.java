package com.cloud.danjjang.common.jwt;

import com.cloud.danjjang.common.apiPayload.code.status.ErrorCode;
import com.cloud.danjjang.common.exception.GeneralException;
import com.cloud.danjjang.common.jwt.filter.JwtAuthenticationFilter;
import com.cloud.danjjang.domain.member.dto.MemberSignDTO;
import com.cloud.danjjang.domain.member.entity.Refresh;
import com.cloud.danjjang.domain.member.repository.RefreshRepository;
import io.jsonwebtoken.ExpiredJwtException;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;

@Transactional
@Slf4j
@Service
@RequiredArgsConstructor
public class LoginService {

    private final RefreshRepository refreshRepository;
    private final TokenProvider tokenProvider;
    private final JwtAuthenticationFilter jwtAuthenticationFilter;
    private final AuthenticationManagerBuilder authenticationManagerBuilder;

    @Value("${jwt.refresh.expire}")
    private Long refreshExpirationTime;

    public TokenDTO login(MemberSignDTO.LoginDTO loginDTO) {

        UsernamePasswordAuthenticationToken authenticationToken =
                new UsernamePasswordAuthenticationToken(loginDTO.getEmail(), loginDTO.getPassword());

        Authentication authentication = authenticationManagerBuilder.getObject().authenticate(authenticationToken);
        return tokenProvider.generateToken(authentication);
    }

    public String issueAccessToken(String username) {
        Authentication authentication = new UsernamePasswordAuthenticationToken(username, null);
        return tokenProvider.generateToken(authentication).getAccessToken();
    }

    public String issueRefreshToken(String email) {
        Authentication authentication = new UsernamePasswordAuthenticationToken(email, null);
        return tokenProvider.generateToken(authentication).getRefreshToken();
    }

    @Transactional
    public String reissueRefreshToken(String email, String refreshToken) {
        refreshRepository.deleteByRefreshToken(refreshToken);
        Authentication authentication = new UsernamePasswordAuthenticationToken(email, null);
        String newRefreshToken = tokenProvider.generateToken(authentication).getRefreshToken();
        saveRefreshToken(email, newRefreshToken, refreshExpirationTime);
        return newRefreshToken;
    }

    @Transactional
    public void revokeRefreshToken(String refreshToken) {
        refreshRepository.deleteByRefreshToken(refreshToken);
    }

    public String validateRefreshToken(HttpServletRequest request) {
        String refreshToken = jwtAuthenticationFilter.resolveToken(request);

        if (refreshToken == null || !refreshRepository.existsByRefreshToken(refreshToken)) {
            throw new GeneralException(ErrorCode.INVALID_TOKEN);
        }

        try {
            tokenProvider.validateToken(refreshToken);
        } catch (ExpiredJwtException e) {
            throw new GeneralException(ErrorCode.EXPIRED_TOKEN);
        }

        return refreshToken;
    }

    private void saveRefreshToken(String email, String refreshToken, Long expirationTime) {
        LocalDateTime date = LocalDateTime.now(ZoneId.systemDefault()).plusSeconds(expirationTime);
        Refresh newRefresh = Refresh.builder()
                .username(email)
                .refreshToken(refreshToken)
                .expiredAt(date)
                .build();
        refreshRepository.save(newRefresh);
    }

    private boolean isTokenExpired(Refresh token) {
        return token.getExpiredAt().isBefore(LocalDateTime.now());  // 만약 expiredAt 필드를 사용하여 비교
    }

}

