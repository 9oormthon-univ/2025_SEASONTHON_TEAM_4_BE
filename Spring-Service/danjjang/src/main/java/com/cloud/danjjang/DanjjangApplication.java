package com.cloud.danjjang;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

@SpringBootApplication
@EnableJpaAuditing
public class DanjjangApplication {

	public static void main(String[] args) {
		SpringApplication.run(DanjjangApplication.class, args);
	}

}
