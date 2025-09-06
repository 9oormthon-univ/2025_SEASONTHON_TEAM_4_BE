package com.cloud.danjjang.domain.member.entity;

import com.cloud.danjjang.common.entity.BaseTimeEntity;
import com.cloud.danjjang.domain.enums.DiabetesType;
import com.cloud.danjjang.domain.enums.Gender;
import com.cloud.danjjang.domain.enums.Sensor;
import com.cloud.danjjang.domain.enums.Status;
import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import lombok.*;

@Entity
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(name = "member")
public class Member extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "member_id")
    private Long id;

    @Email
    @Column(nullable = false)
    private String email;

    @Column(nullable = false)
    private String password;

    @Column(nullable = false)
    private Long birth;

    @Column(nullable = false, length = 50)
    private String username;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Gender gender;

    @Column(nullable = false)
    private Float height;

    @Column(nullable = false)
    private Float weight;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DiabetesType diabetesType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Sensor sensor;

    private String code;

    @Builder.Default
    @Enumerated(EnumType.STRING)
    private Status status = Status.ACTIVE;




}
