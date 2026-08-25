---
title: "dev | software-development-kits-templates"
description: "sugar, make me happier, make more hacker."
date: "2023-06-29T03:37:00.000Z"
updated: "2024-03-19T02:10:38.000Z"
tags: []
draft: false
layout: "post"
slug: "sdk-patterns"
---

## software-development-kits

## idk

### python

-   decorator

    如果想知道 `print_prime` 总共花费的时间

    ```python
    def is_prime(n):
        if n <= 1: return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0: return False
        return True
    
    def print_prime(max_num):
        import time
        t1 = time.time()
        count = 0
        for num in range(2, max_num + 1):
            if is_prime(num):
                count += 1
                print(num)
    	t2 = time.time()
        print('time spend: {}; total: {}'.format(t2 - t1, count))
        
    def print_prime2(max_num):
        import time
        t1 = time.time()
        count = 0
        for num in range(2, max_num + 1 + 10000):
            if is_prime(num):
                count += 1
                print(num)
    	t2 = time.time()
        print('time spend: {}; total: {}'.format(t2 - t1, count))
    
    max_num = 10000
    print_prime(max_num)
    ```

    使用装饰器后转为以下内容

    ```python
    def print_prime_decorator(func):
    	def wrapper(*args):
    		import time
    		t1 = time.time()
    		result = func(*args)
    		t2 = time.time()
    		print('time spend: {}'.format(t2 - t1))
    		return result
    	return wrapper
    
    def is_prime(n):
    	if n <= 1: return False
    	for i in range(2, int(n**0.5) + 1):
    		if n % i == 0: return False
    	return True
    
    @print_prime_decorator
    def print_prime(max_num):
    	for num in range(2, max_num + 1):
    		if is_prime(num):
    			print(num)
    
    @print_prime_decorator
    def print_prime2(max_num):
        for num in range(2, max_num + 1 + 10000):
            if is_prime(num):
                print(num)
    
    max_num = 10000
    print_prime(max_num)
    print_prime2(max_num)
    ```

    函数执行时，会先进入到 wrapper 中，情况适用于需要大量重复相同的代码，如此一来只需要在函数前添加一个装饰器函数即可，提升代码可读性

## sdk

这里是一个经典的 sdk 通用模板，通常由以下一些或全部模块组成：

-   代码规范，code samples；给出一些使用该 sdk 进行开发时，应该使用的代码规范或代码开发范例
-   常用库、框架等，code libraries（framework）；使用 sdk 时需要重复用到的一些库函数，脚手架工具等
-   测试、性能分析工具，testing and analytics tools；这些工具用于在使用 sdk 开发时，对项目进行测试和性能分析
-   使用、操作文档，documentation；开发参考文档
-   调试器，debuggers；方便开发者在使用 sdk 时进行一些除错等
-   编译器，compiler；整个 sdk 开发的核心（可选）

## references

1.   sdk 简介，[SDK vs. API: What’s the Difference?](https://www.ibm.com/cloud/blog/sdk-vs-api)
2.
