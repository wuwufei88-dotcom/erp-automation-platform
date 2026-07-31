import React from "react";

interface ContainerProps {
  children: React.ReactNode;
}

export default function Container({ children }: ContainerProps) {
  return (
    <div
      style={{
        maxWidth: 1200,
        margin: "0 auto",
        padding: "0 24px",
        width: "100%",
      }}
    >
      {children}
    </div>
  );
}
