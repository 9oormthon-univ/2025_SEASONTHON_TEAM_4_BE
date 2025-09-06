package com.cloud.danjjang.domain.member.annotation;

import com.cloud.danjjang.common.apiPayload.code.status.ErrorCode;
import com.cloud.danjjang.common.exception.handler.GeneralHandler;
import com.cloud.danjjang.common.jwt.TokenProvider;
import com.cloud.danjjang.domain.member.entity.Member;
import com.cloud.danjjang.domain.member.repository.MemberRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.MethodParameter;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

@Component
@RequiredArgsConstructor
@Slf4j
public class AuthUserArgumentResolver implements HandlerMethodArgumentResolver {

    private final TokenProvider tokenProvider;
    private final MemberRepository memberRepository;

    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        boolean hasAnnotation = parameter.hasParameterAnnotation(AuthUser.class);
        boolean isMemberType = Member.class.isAssignableFrom(parameter.getParameterType());

        return hasAnnotation && isMemberType;
    }

    @Override
    public Object resolveArgument(MethodParameter parameter, ModelAndViewContainer mavContainer, NativeWebRequest webRequest,
                                  WebDataBinderFactory binderFactory) {
        String bearer = webRequest.getHeader("Authorization");
        assert bearer != null;
        String token = bearer.substring(7);
        String memberIdentifier = tokenProvider.getAuthenticationFromAccessToken(token).getName();
        return memberRepository.findByEmail(memberIdentifier).orElseThrow(() -> new GeneralHandler(ErrorCode.MEMBER_NOT_FOUND));
    }
}
