import React, { createContext, useContext, useState, useEffect } from 'react';

const PermissionContext = createContext();

export const usePermissions = () => {
    const context = useContext(PermissionContext);
    if (!context) {
        throw new Error('usePermissions must be used within PermissionProvider');
    }
    return context;
};

export const PermissionProvider = ({ children }) => {
    const [permissions, setPermissions] = useState({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const checkPermission = (page, action) => {
        const user = JSON.parse(localStorage.getItem('user'));
        
        // Super admin has all permissions
        if (user?.is_superuser) return true;
        
        // Check cached permissions
        const pagePermissions = permissions[page];
        if (!pagePermissions) return false;
        
        // Hierarchical permission check
        switch (action) {
            case 'view':
                return pagePermissions.can_view || pagePermissions.can_edit || 
                       pagePermissions.can_create || pagePermissions.can_delete;
            case 'create':
                return pagePermissions.can_create;
            case 'edit':
                return pagePermissions.can_edit || pagePermissions.can_delete;
            case 'delete':
                return pagePermissions.can_delete;
            default:
                return false;
        }
    };

    const refreshPermissions = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/user/accessible-pages/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setPermissions(data);
                setError(null);
            }
        } catch (err) {
            setError('Failed to load permissions');
        } finally {
            setLoading(false);
        }
    };

    return (
        <PermissionContext.Provider value={{
            permissions,
            checkPermission,
            refreshPermissions,
            loading,
            error
        }}>
            {children}
        </PermissionContext.Provider>
    );
};