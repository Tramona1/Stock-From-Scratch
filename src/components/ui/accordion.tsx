"use client"

import * as React from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface AccordionItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  trigger: React.ReactNode
}

const AccordionItem = React.forwardRef<HTMLDivElement, AccordionItemProps>(
  ({ className, trigger, children, value, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("border-b", className)}
        data-value={value}
        {...props}
      >
        {trigger}
        {children}
      </div>
    )
  }
)
AccordionItem.displayName = "AccordionItem"

interface AccordionTriggerProps extends React.HTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  isOpen?: boolean
  onClick?: () => void
}

const AccordionTrigger = React.forwardRef<HTMLButtonElement, AccordionTriggerProps>(
  ({ className, children, isOpen, onClick, ...props }, ref) => (
    <button
      ref={ref}
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-center justify-between py-4 font-medium transition-all hover:underline",
        className
      )}
      {...props}
    >
      {children}
      <ChevronDown 
        className={cn(
          "h-4 w-4 shrink-0 transition-transform duration-200",
          isOpen ? "rotate-180" : "rotate-0"
        )} 
      />
    </button>
  )
)
AccordionTrigger.displayName = "AccordionTrigger"

interface AccordionContentProps extends React.HTMLAttributes<HTMLDivElement> {
  isOpen?: boolean
}

const AccordionContent = React.forwardRef<HTMLDivElement, AccordionContentProps>(
  ({ className, children, isOpen, ...props }, ref) => {
    if (!isOpen) return null;
    
    return (
      <div
        ref={ref}
        className={cn("overflow-hidden text-sm", className)}
        {...props}
      >
        <div className="pb-4 pt-0">{children}</div>
      </div>
    )
  }
)
AccordionContent.displayName = "AccordionContent"

interface AccordionProps extends React.HTMLAttributes<HTMLDivElement> {
  type?: "single" | "multiple"
  collapsible?: boolean
  defaultValue?: string
}

const Accordion = React.forwardRef<HTMLDivElement, AccordionProps>(
  ({ children, className, type = "single", collapsible = false, defaultValue, ...props }, ref) => {
    const [openItems, setOpenItems] = React.useState<string[]>(
      defaultValue ? [defaultValue] : []
    );

    const handleItemClick = (value: string) => {
      if (type === "single") {
        if (collapsible && openItems.includes(value)) {
          setOpenItems([]);
        } else {
          setOpenItems([value]);
        }
      } else {
        if (openItems.includes(value)) {
          setOpenItems(openItems.filter(item => item !== value));
        } else {
          setOpenItems([...openItems, value]);
        }
      }
    };

    // Clone children with additional props
    const enhancedChildren = React.Children.map(children, child => {
      if (!React.isValidElement(child)) return child;

      const value = child.props.value;
      const isOpen = value ? openItems.includes(value) : false;

      // Clone the trigger with isOpen prop
      const enhancedTrigger = React.cloneElement(
        child.props.trigger as React.ReactElement,
        {
          isOpen,
          onClick: () => handleItemClick(value)
        }
      );

      // Clone the content with isOpen prop
      const content = React.Children.map(child.props.children, contentChild => {
        if (!React.isValidElement(contentChild)) return contentChild;
        // Use type assertion to fix TypeScript error
        return React.cloneElement(
          contentChild, 
          { isOpen } as React.JSX.IntrinsicAttributes & { isOpen: boolean }
        );
      });

      // Use type assertion to fix TypeScript error
      return React.cloneElement(
        child, 
        {
          trigger: enhancedTrigger,
          children: content
        } as React.JSX.IntrinsicAttributes & { 
          trigger: React.ReactElement;
          children: React.ReactNode;
        }
      );
    });

    return (
      <div 
        ref={ref} 
        className={cn("w-full", className)}
        {...props}
      >
        {enhancedChildren}
      </div>
    );
  }
);
Accordion.displayName = "Accordion";

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent } 