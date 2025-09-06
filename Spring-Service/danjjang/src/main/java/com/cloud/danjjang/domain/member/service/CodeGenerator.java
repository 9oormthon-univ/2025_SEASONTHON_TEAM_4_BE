package com.cloud.danjjang.domain.member.service;

import java.security.SecureRandom;

public final class CodeGenerator {
    private static final char[] CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789".toCharArray();
    private static final SecureRandom RNG = new SecureRandom();

    private CodeGenerator() {}

    public static String next(int len) {
        char[] buf = new char[len];
        for (int i = 0; i < len; i++) buf[i] = CHARS[RNG.nextInt(CHARS.length)];
        return new String(buf);
    }
}
