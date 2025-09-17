package com.cloud.danjjang.domain.parent.entity;

import com.cloud.danjjang.common.entity.BaseTimeEntity;
import com.cloud.danjjang.domain.member.entity.Member;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Parent extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
}
