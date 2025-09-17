package com.cloud.danjjang.domain.parentChild.entity;

import com.cloud.danjjang.common.entity.BaseTimeEntity;
import com.cloud.danjjang.domain.member.entity.Member;
import com.cloud.danjjang.domain.parent.entity.Parent;
import jakarta.persistence.*;
import lombok.*;

@Getter
@Builder
@NoArgsConstructor
@Entity
@Table(name = "parent-child")
@AllArgsConstructor
public class ParentChild extends BaseTimeEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id")
    private Member member;

    @Setter
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_id")
    private Parent parent;
}
