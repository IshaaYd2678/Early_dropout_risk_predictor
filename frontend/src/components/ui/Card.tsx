// Production-grade Card Component
import React from 'react';
import { clsx } from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
}

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  border?: boolean;
}

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  border?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding = 'md', hover = false, ...props }, ref) => {
    const baseClasses = [
      'rounded-lg transition-all duration-200',
    ];

    const variantClasses = {
      default: [
        'bg-white border border-gray-200 shadow-sm',
        'dark:bg-gray-800 dark:border-gray-700',
      ],
      elevated: [
        'bg-white shadow-lg border border-gray-100',
        'dark:bg-gray-800 dark:border-gray-700',
      ],
      outlined: [
        'bg-white border-2 border-gray-200',
        'dark:bg-gray-800 dark:border-gray-600',
      ],
      filled: [
        'bg-gray-50 border border-gray-200',
        'dark:bg-gray-900 dark:border-gray-700',
      ],
    };

    const paddingClasses = {
      none: '',
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6',
      xl: 'p-8',
    };

    const hoverClasses = hover ? [
      'hover:shadow-md hover:-translate-y-0.5',
      'cursor-pointer',
    ] : [];

    return (
      <div
        ref={ref}
        className={clsx(
          baseClasses,
          variantClasses[variant],
          paddingClasses[padding],
          hoverClasses,
          className
        )}
        {...props}
      />
    );
  }
);

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, border = true, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        'flex flex-col space-y-1.5',
        border && 'pb-4 border-b border-gray-200 dark:border-gray-700',
        className
      )}
      {...props}
    />
  )
);

const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={clsx(
        'text-lg font-semibold leading-none tracking-tight',
        'text-gray-900 dark:text-gray-100',
        className
      )}
      {...props}
    />
  )
);

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={clsx(
        'text-sm text-gray-600 dark:text-gray-400',
        className
      )}
      {...props}
    />
  )
);

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('pt-0', className)}
      {...props}
    />
  )
);

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, border = true, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        'flex items-center',
        border && 'pt-4 border-t border-gray-200 dark:border-gray-700',
        className
      )}
      {...props}
    />
  )
);

Card.displayName = 'Card';
CardHeader.displayName = 'CardHeader';
CardTitle.displayName = 'CardTitle';
CardDescription.displayName = 'CardDescription';
CardContent.displayName = 'CardContent';
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };