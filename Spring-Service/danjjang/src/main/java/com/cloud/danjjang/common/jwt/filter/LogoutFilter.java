package com.cloud.danjjang.common.jwt.filter;

import com.cloud.danjjang.common.apiPayload.ApiResponse;
import com.cloud.danjjang.common.apiPayload.code.status.ErrorCode;
import com.cloud.danjjang.common.apiPayload.code.status.SuccessCode;
import com.cloud.danjjang.common.exception.GeneralException;
import com.cloud.danjjang.common.jwt.LoginService;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@RequiredArgsConstructor
public class LogoutFilter extends OncePerRequestFilter {

    private final LoginService loginService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {

        if (!(request.getMethod().equals("POST") && request.getRequestURI().matches("/api/users/logout"))) {
            filterChain.doFilter(request, response);
            return;
        }

        try {
            String refreshToken = loginService.validateRefreshToken(request);
            loginService.revokeRefreshToken(refreshToken);

            writeOutput(request, response, HttpServletResponse.SC_OK, ApiResponse.onSuccess(SuccessCode._OK));
        } catch (Exception e) {
            writeOutput(request, response, HttpServletResponse.SC_BAD_REQUEST, ApiResponse.ofFailure(ErrorCode._BAD_REQUEST, null));
        }
    }

    private void writeOutput(HttpServletRequest request, HttpServletResponse response, int statusCode, ApiResponse<?> data) {
        try {
            response.setStatus(statusCode);
            response.setHeader("Content-Type", "application/json");
            response.getOutputStream().write(objectMapper.writeValueAsBytes(data));
        } catch (Exception e) {
            GeneralException newException = new GeneralException(ErrorCode.OUTPUT_ERROR);
            request.setAttribute("exception", newException);
            throw newException;
        }
    }
}