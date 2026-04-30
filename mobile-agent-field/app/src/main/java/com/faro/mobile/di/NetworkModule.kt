package com.faro.mobile.di

import android.content.Context
import com.faro.mobile.BuildConfig
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.session.SessionStore
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.runBlocking
import okhttp3.Cache
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

/**
 * Retry configuration for OkHttpClient.
 * Uses OkHttp built-in retryOnConnectionFailure for transient errors.
 */
object RetryConfig {
    const val MAX_RETRIES = 3
    const val INITIAL_DELAY_MS = 1000L
    const val BACKOFF_MULTIPLIER = 2.0
    const val MAX_DELAY_MS = 10000L

    // HTTP status codes that should trigger additional retry
    private val RETRYABLE_STATUS_CODES = setOf(429, 500, 501, 502, 503, 504)

    fun shouldRetry(response: Response?): Boolean {
        if (response == null) return true
        return response.code in RETRYABLE_STATUS_CODES
    }

    fun calculateDelay(attempt: Int): Long {
        val delay = (INITIAL_DELAY_MS * Math.pow(BACKOFF_MULTIPLIER.toDouble(), (attempt - 1).toDouble())).toLong()
        return delay.coerceAtMost(MAX_DELAY_MS)
    }
}

/**
 * Auth interceptor that adds Bearer token to requests.
 * Uses runBlocking only for initial token fetch, then caches locally.
 */
class AuthTokenInterceptor(
    private val sessionStore: SessionStore
) : Interceptor {
    // Cache the token in memory to avoid repeated DataStore reads
    @Volatile
    private var cachedToken: String? = null
    
    @Volatile
    private var tokenExpiry: Long = 0L
    
    @Synchronized
    fun updateToken(token: String?, expiry: Long) {
        cachedToken = token
        tokenExpiry = expiry
    }

    @Synchronized
    fun clearToken() {
        cachedToken = null
        tokenExpiry = 0L
    }

    @Throws(IOException::class)
    override fun chain(chain: Interceptor.Chain): Response {
        val request = chain.request()
        
        // Check if cached token is valid
        val token = synchronized(this) {
            if (cachedToken.isNullOrBlank()) {
                // Fetch from sessionStore (non-blocking on subsequent calls)
                runBlocking {
                    sessionStore.getAccessToken()
                }
            } else {
                cachedToken
            }
        }
        
        val requestBuilder = request.newBuilder()
        if (!token.isNullOrBlank()) {
            requestBuilder.addHeader("Authorization", "Bearer $token")
        }
        
        return chain.proceed(requestBuilder.build())
    }
}

/**
 * Interceptor that logs HTTP errors for debugging.
 */
class ErrorLoggingInterceptor : Interceptor {
    @Throws(IOException::class)
    override fun chain(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val response = try {
            chain.proceed(request)
        } catch (e: IOException) {
            android.util.Log.e("NetworkModule", "Network error: ${e.message}")
            throw e
        }

        if (!response.isSuccessful) {
            android.util.Log.w("NetworkModule", "HTTP ${response.code} for ${request.url}")
        }

        return response
    }
}

/**
 * Interceptor that adds common headers.
 */
class HeaderInterceptor : Interceptor {
    @Throws(IOException::class)
    override fun chain(chain: Interceptor.Chain): Response {
        val request = chain.request().newBuilder()
            .addHeader("Accept", "application/json")
            .addHeader("Connection", "keep-alive")
            .build()
        
        return chain.proceed(request)
    }
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    private const val CACHE_SIZE_BYTES = 10L * 1024L * 1024L // 10 MB

    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor {
        return HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(
        loggingInterceptor: HttpLoggingInterceptor,
        sessionStore: SessionStore,
        context: Context,
    ): OkHttpClient {
        // Setup cache directory
        val cacheDir = File(context.cacheDir, "http_cache")
        val cache = Cache(cacheDir, CACHE_SIZE_BYTES)

        return OkHttpClient.Builder()
            // HTTP cache - reduz dados redundantes
            .cache(cache)
            // Auth token interceptor
            .addInterceptor(AuthTokenInterceptor(sessionStore))
            // Common headers
            .addInterceptor(HeaderInterceptor())
            // Error logging
            .addInterceptor(ErrorLoggingInterceptor())
            // Network logging
            .addInterceptor(loggingInterceptor)
            // Timeouts
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            // Retry on connection failure (OkHttp built-in)
            .retryOnConnectionFailure(true)
            .build()
    }

    @Provides
    @Singleton
    fun provideRetrofit(
        client: OkHttpClient,
        context: Context
    ): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideFaroMobileApi(retrofit: Retrofit): FaroMobileApi {
        return retrofit.create(FaroMobileApi::class.java)
    }
}