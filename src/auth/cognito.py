"""
AWS Cognito authentication module.

Handles user login, logout, token refresh, and session management
using Cognito User Pools with USERNAME_PASSWORD_AUTH flow.
"""

import boto3
from botocore.exceptions import ClientError


class AuthError(Exception):
    """Raised when authentication fails."""

    pass


class CognitoAuth:
    def __init__(self, user_pool_id: str, client_id: str, region: str):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.client = boto3.client("cognito-idp", region_name=region)

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a user with email and password.

        Returns:
            dict with access_token, id_token, refresh_token, expires_in

        Raises:
            AuthError: On invalid credentials or unconfirmed account.
        """
        try:
            response = self.client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                },
                ClientId=self.client_id,
            )
            result = response["AuthenticationResult"]
            return {
                "access_token": result["AccessToken"],
                "id_token": result["IdToken"],
                "refresh_token": result["RefreshToken"],
                "expires_in": result["ExpiresIn"],
            }
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "NotAuthorizedException":
                raise AuthError("Incorrect email or password.")
            if code == "UserNotFoundException":
                raise AuthError("No account found with that email.")
            if code == "UserNotConfirmedException":
                raise AuthError(
                    "Account not confirmed. Check your email for a verification link."
                )
            if code == "PasswordResetRequiredException":
                raise AuthError("Password reset required. Check your email.")
            raise AuthError(f"Authentication failed: {e.response['Error']['Message']}")

    def get_user(self, access_token: str) -> dict:
        """
        Get user attributes from a valid access token.

        Returns:
            dict with email and other user attributes.
        """
        try:
            response = self.client.get_user(AccessToken=access_token)
            attrs = {a["Name"]: a["Value"] for a in response["UserAttributes"]}
            return {
                "username": response["Username"],
                "email": attrs.get("email", ""),
                "email_verified": attrs.get("email_verified", "false") == "true",
            }
        except ClientError as e:
            raise AuthError(
                f"Failed to get user info: {e.response['Error']['Message']}"
            )

    def refresh_session(self, refresh_token: str) -> dict:
        """Refresh an expired access token using the refresh token."""
        try:
            response = self.client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token},
                ClientId=self.client_id,
            )
            result = response["AuthenticationResult"]
            return {
                "access_token": result["AccessToken"],
                "id_token": result["IdToken"],
                "expires_in": result["ExpiresIn"],
            }
        except ClientError as e:
            raise AuthError(f"Session refresh failed: {e.response['Error']['Message']}")

    def logout(self, access_token: str) -> None:
        """Invalidate the user's tokens (global sign-out)."""
        try:
            self.client.global_sign_out(AccessToken=access_token)
        except ClientError:
            pass  # Token may already be expired — that's fine

    def signup(self, email: str, password: str) -> None:
        """
        Register a new user. They will receive a confirmation email.

        Raises:
            AuthError: If the email is already registered or password is too weak.
        """
        try:
            self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=[{"Name": "email", "Value": email}],
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "UsernameExistsException":
                raise AuthError("An account with this email already exists.")
            if code == "InvalidPasswordException":
                raise AuthError(
                    f"Password does not meet requirements: {e.response['Error']['Message']}"
                )
            raise AuthError(f"Sign up failed: {e.response['Error']['Message']}")

    def confirm_signup(self, email: str, code: str) -> None:
        """Confirm a user's account with the verification code sent to their email."""
        try:
            self.client.confirm_sign_up(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=code,
            )
        except ClientError as e:
            raise AuthError(f"Confirmation failed: {e.response['Error']['Message']}")

    def forgot_password(self, email: str) -> None:
        """Initiate the forgot password flow — sends a reset code to the user's email."""
        try:
            self.client.forgot_password(ClientId=self.client_id, Username=email)
        except ClientError as e:
            raise AuthError(f"Password reset failed: {e.response['Error']['Message']}")

    def confirm_forgot_password(self, email: str, code: str, new_password: str) -> None:
        """Complete the password reset with the code from email."""
        try:
            self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=code,
                Password=new_password,
            )
        except ClientError as e:
            raise AuthError(
                f"Password reset confirmation failed: {e.response['Error']['Message']}"
            )
