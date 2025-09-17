package com.cloud.danjjang.domain.member.controller;

import com.cloud.danjjang.common.apiPayload.ApiResponse;
import com.cloud.danjjang.common.apiPayload.code.status.SuccessCode;
import com.cloud.danjjang.common.jwt.LoginService;
import com.cloud.danjjang.common.jwt.TokenDTO;
import com.cloud.danjjang.domain.member.annotation.AuthUser;
import com.cloud.danjjang.domain.member.dto.MemberRequestDTO;
import com.cloud.danjjang.domain.member.dto.MemberResponseDTO;
import com.cloud.danjjang.domain.member.dto.MemberSignDTO;
import com.cloud.danjjang.domain.member.dto.RefreshTokenDTO;
import com.cloud.danjjang.domain.member.entity.Member;
import com.cloud.danjjang.domain.member.service.MemberMapper;
import com.cloud.danjjang.domain.member.service.MemberService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import static com.cloud.danjjang.common.apiPayload.code.status.SuccessCode._SIGNUP_SUCCESS;

@Tag(name = "유저 관련 API", description = "유저 관련 API입니다")
@RequiredArgsConstructor
@RequestMapping("/api/users")
@RestController
public class MemberController {

    private final MemberService memberService;
    private final LoginService loginService;

    @Operation(summary = "회원가입 API")
    @PostMapping("/signup")
    public ApiResponse<RefreshTokenDTO> joinByLoginId(HttpServletResponse response,
                                                      @Valid @RequestBody MemberSignDTO.SignUpDTO requestDto) {
        return ApiResponse.of(_SIGNUP_SUCCESS, memberService.insertMember(response, requestDto));
    }

    @Operation(summary = "로그인 API")
    @PostMapping("/login")
    public ApiResponse<TokenDTO> login(@Valid @RequestBody MemberSignDTO.LoginDTO request) {
        //Filter에서 작동, swagger 틀만 작성
        MemberSignDTO.LoginDTO loginDTO = new MemberSignDTO.LoginDTO(request.getEmail(), request.getPassword());
        return ApiResponse.onSuccess(loginService.login(loginDTO));
    }

    @Operation(summary = "토큰 재발급 api", description = "Cookie에 기존 refresh 토큰 필요, 헤더의 Authorization에 access 토큰, 바디(쿠키)에 refresh 토큰 반환")
    @PostMapping("/reissue")
    public ApiResponse<RefreshTokenDTO> reissue(HttpServletRequest request, HttpServletResponse response) {
        String newRefreshToken = memberService.reissueToken(request, response);
        return ApiResponse.of(SuccessCode._OK, MemberMapper.toRefreshToken(newRefreshToken));
    }

    @PostMapping("/logout")
    public ApiResponse<?> logout() {
        // Filter에서 작동하지만, Swagger 위해서 틀만 작성
        return ApiResponse.onSuccess(SuccessCode._OK);
    }

    @Operation(summary = "부모 로그인 api")
    @PostMapping("/auth/parent-login")
    public ApiResponse<TokenDTO> parentLogin(@RequestParam String code, HttpServletResponse response) {
        return ApiResponse.onSuccess(memberService.parentLoginByCode(code, response));
    }

    @Operation(summary = "마이페이지 조회 api")
    @GetMapping("/my-page")
    public ApiResponse<MemberResponseDTO.MyPageResponseDTO> myPage(@AuthUser Member member){
        return ApiResponse.onSuccess(memberService.getMemberprofile(member));
    }

    @Operation(summary = "이름, 생년월일, 성별, 키, 몸무게 바꾸기")
    @PostMapping("/setting")
    public ApiResponse<MemberResponseDTO.MemberSettingDTO> profileSetting(@AuthUser Member member, @Valid @RequestBody MemberRequestDTO.MemberProfileDTO requestDto){
        return ApiResponse.onSuccess(memberService.profileSetting(member, requestDto));
    }

    @Operation(summary = "센서 설정 바꾸기")
    @PostMapping("/setting/sensor")
    public ApiResponse<MemberResponseDTO.MemberSettingDTO> sensorSetting(@AuthUser Member member, @Valid @RequestBody MemberRequestDTO.MemberSensorDTO requestDto){
        return ApiResponse.onSuccess(memberService.sensorSetting(member, requestDto));
    }
}