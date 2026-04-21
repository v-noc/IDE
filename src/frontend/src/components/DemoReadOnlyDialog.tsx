import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ShieldAlert } from "lucide-react";

interface DemoReadOnlyDialogProps {
    isOpen: boolean;
    onClose: () => void;
}

export function DemoReadOnlyDialog({ isOpen, onClose }: DemoReadOnlyDialogProps) {
    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-amber-100">
                        <ShieldAlert className="h-6 w-6 text-amber-600" />
                    </div>
                    <DialogTitle className="text-center text-xl font-bold">
                        Demo Read-Only
                    </DialogTitle>
                    <DialogDescription className="text-center text-base pt-2">
                        This is a preview demo environment. All write operations (creating, editing, and deleting) are currently disabled.
                    </DialogDescription>
                </DialogHeader>
                <DialogFooter className="sm:justify-center mt-4">
                    <Button
                        type="button"
                        onClick={onClose}
                        className="w-full sm:w-32 bg-amber-600 hover:bg-amber-700 text-white font-medium shadow-sm transition-colors py-2"
                    >
                        Got it
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
