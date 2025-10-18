import React from 'react';

const Icon = ({ name, className = '', size = 24, ...props }) => {
  return (
    <img
      src={`/icons/${name}.svg`}
      alt={`${name} icon`}
      className={className}
      style={{ width: size, height: size }}
      {...props}
    />
  );
};

export default Icon;

