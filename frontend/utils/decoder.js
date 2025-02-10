export const decodeToken = (token) => {
  if (!token || token.split(".").length !== 3) {
    console.error("Invalid token format:", token);
    return null;
  }

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload;
  } catch (error) {
    console.error("Error decoding token:", error);
    console.error("Token:", token);
    return null;
  }
};
