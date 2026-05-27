"""
Unit tests for security module

Tests password hashing, JWT token generation, and verification.
"""

import pytest
from datetime import timedelta
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_token, verify_refresh_token,
    TokenData
)


class TestPasswordHashing:
    """Tests for password hashing functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!@#"
        hashed = hash_password(password)
        
        # Hashed password should be different from original
        assert hashed != password
        # Hashed password should be longer (bcrypt output)
        assert len(hashed) > len(password)
    
    def test_verify_correct_password(self):
        """Test verifying correct password"""
        password = "TestPassword123!@#"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password"""
        password = "TestPassword123!@#"
        wrong_password = "WrongPassword123!@#"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) == False
    
    def test_different_hashes_same_password(self):
        """Test that same password generates different hashes"""
        password = "TestPassword123!@#"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different (bcrypt includes salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True


class TestAccessTokenGeneration:
    """Tests for access token generation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        secret_key = "test_secret_key_min_32_chars_long"
        user_id = 1
        email = "test@example.com"
        role = "user"
        
        token, expiration = create_access_token(
            user_id=user_id,
            email=email,
            role=role,
            secret_key=secret_key,
        )
        
        assert token is not None
        assert len(token) > 0
        assert expiration > 0
    
    def test_verify_access_token(self):
        """Test access token verification"""
        secret_key = "test_secret_key_min_32_chars_long"
        user_id = 1
        email = "test@example.com"
        role = "user"
        
        token, _ = create_access_token(
            user_id=user_id,
            email=email,
            role=role,
            secret_key=secret_key,
        )
        
        token_data = verify_token(
            token=token,
            secret_key=secret_key,
        )
        
        assert token_data.user_id == user_id
        assert token_data.email == email
        assert token_data.role == role
    
    def test_verify_token_wrong_secret(self):
        """Test token verification with wrong secret"""
        secret_key = "test_secret_key_min_32_chars_long"
        wrong_key = "wrong_secret_key_min_32_chars_long"
        
        token, _ = create_access_token(
            user_id=1,
            email="test@example.com",
            role="user",
            secret_key=secret_key,
        )
        
        with pytest.raises(Exception):
            verify_token(
                token=token,
                secret_key=wrong_key,
            )


class TestRefreshTokenGeneration:
    """Tests for refresh token generation"""
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        secret_key = "test_secret_key_min_32_chars_long"
        user_id = 1
        
        token, expiration = create_refresh_token(
            user_id=user_id,
            secret_key=secret_key,
        )
        
        assert token is not None
        assert len(token) > 0
        assert expiration > 0
    
    def test_verify_refresh_token(self):
        """Test refresh token verification"""
        secret_key = "test_secret_key_min_32_chars_long"
        user_id = 1
        
        token, _ = create_refresh_token(
            user_id=user_id,
            secret_key=secret_key,
        )
        
        verified_user_id = verify_refresh_token(
            token=token,
            secret_key=secret_key,
        )
        
        assert verified_user_id == user_id
    
    def test_verify_access_token_as_refresh_token(self):
        """Test that access token cannot be used as refresh token"""
        secret_key = "test_secret_key_min_32_chars_long"
        
        access_token, _ = create_access_token(
            user_id=1,
            email="test@example.com",
            role="user",
            secret_key=secret_key,
        )
        
        # Should fail because access token has type='access' not 'refresh'
        with pytest.raises(Exception):
            verify_refresh_token(
                token=access_token,
                secret_key=secret_key,
            )


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
